package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"sort"
	"strings"
	"sync"
)

var ignoredFields map[string]bool = map[string]bool{
	"statistics":  true,
	"periodicity": true,
	"completedAt": true,
	"stackTrace":  true,
}

func main() {
	fmt.Println("Transiter comparison tool")

	session := newSession("http://localhost:8081", "http://localhost:8005", 1)
	session.start("systems")
}

type session struct {
	baseUrl1 string
	baseUrl2 string

	seenUrls      map[string]bool
	seenUrlsMutex sync.Mutex

	nextUrls chan string
}

func newSession(baseUrl1, baseUrl2 string, maxConcurrentRequests int) *session {
	return &session{
		baseUrl1: baseUrl1,
		baseUrl2: baseUrl2,
		seenUrls: map[string]bool{},
		nextUrls: make(chan string, 10000),
	}
}

func (s *session) start(relativeUrl string) {
	s.seenUrls[relativeUrl] = true
	s.nextUrls <- relativeUrl
	for len(s.nextUrls) > 0 {
		nextUrl := <-s.nextUrls
		s.visit(nextUrl)
	}
}

func (s *session) visit(relativeUrl string) {
	fmt.Printf("Visiting /%s\n", relativeUrl)

	rawResponse1, err := get(s.baseUrl1, relativeUrl)
	if err != nil {
		panic(fmt.Sprintf("Failed to read %s\n Error: %s", s.baseUrl1+"/"+relativeUrl, err))
	}
	response1, err := unmarshal(rawResponse1)
	if err != nil {
		panic(fmt.Sprintf("Failed to unmarshal response: %s\nResponse:\n%s", err, string(rawResponse1)))
	}
	rawResponse2, err := get(s.baseUrl2, relativeUrl)
	if err != nil {
		panic(fmt.Sprintf("Failed to read %s\nError: %s", s.baseUrl2+"/"+relativeUrl, err))
	}
	response2, err := unmarshal(rawResponse2)
	if err != nil {
		panic(fmt.Sprintf("Failed to unmarshal response: %s\nResponse:\n%s", err, string(rawResponse2)))
	}
	if err := compare(response1, response2, relativeUrl); err != nil {
		panic(fmt.Sprintf("response 1:\n%s\nresponse 2:\n%s\nerror at URL: /%s\nvalues do not match for field: %s\nerror message: %s\n",
			string(rawResponse1)[:5000], string(rawResponse2)[:5000], relativeUrl, err.field, err.note,
		))
	}
	potentiallyNewUrls := extractUrls(s.baseUrl2, response2)

	var newUrls []string
	s.seenUrlsMutex.Lock()
	for _, potentiallyNewUrl := range potentiallyNewUrls {
		if s.seenUrls[potentiallyNewUrl] {
			continue
		}
		s.seenUrls[potentiallyNewUrl] = true
		newUrls = append(newUrls, potentiallyNewUrl)
	}
	s.seenUrlsMutex.Unlock()

	sort.Strings(newUrls)
	for _, newUrl := range newUrls {
		s.nextUrls <- newUrl
	}
}

func get(baseUrl, relativeUrl string) ([]byte, error) {
	url := baseUrl + "/" + relativeUrl
	client := &http.Client{}
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("X-Transiter-Host", baseUrl)
	res, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	if res.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("bad status: %d", res.StatusCode)
	}
	body, err := io.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}
	return body, nil
}

type jsonValue struct {
	Slice   []*jsonValue
	Map     map[string]*jsonValue
	Str     *string
	Int     *int
	Float64 *float64
}

func (j *jsonValue) String() string {
	if j.Slice != nil {
		var b strings.Builder
		b.WriteString("[")
		for _, elem := range j.Slice {
			b.WriteString(elem.String() + ", ")
		}
		b.WriteString("]")
		return b.String()
	}
	if j.Map != nil {
		var keys []string
		for key := range j.Map {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		var b strings.Builder
		b.WriteString("{")
		for _, key := range keys {
			value := j.Map[key]
			if key == "href" {
				lhsP, err := url.Parse(*value.Str)
				if err != nil {
					panic("Could not parse url in String()")
				}
				b.WriteString(key + ": " + lhsP.Path + ", ")
				continue
			}
			b.WriteString(key + ": " + value.String() + ", ")
		}
		b.WriteString("}")
		return b.String()
	}
	if j.Str != nil {
		return *j.Str
	}
	panic("Don't know to write string")
}

func unmarshal(data []byte) (*jsonValue, error) {
	var mapResult map[string]interface{}
	if err := json.Unmarshal(data, &mapResult); err == nil {
		return parse(mapResult), nil
	}
	var sliceResult []interface{}
	if err := json.Unmarshal(data, &sliceResult); err == nil {
		return parse(sliceResult), err
	}
	return nil, fmt.Errorf("unable to unmarshal JSON response")
}

func parse(data interface{}) *jsonValue {
	var result jsonValue
	switch d := data.(type) {
	case map[string]interface{}:
		result.Map = map[string]*jsonValue{}
		for key, rawVal := range d {
			if rawVal == nil {
				continue
			}
			key = snakeCaseToCamelCase(key)
			result.Map[key] = parse(rawVal)
		}
	case []interface{}:
		result.Slice = []*jsonValue{}
		for _, rawVal := range d {
			result.Slice = append(result.Slice, parse(rawVal))
		}
	//case int:
	//		s := fmt.Sprintf("%d", d)
	//result.String = &s
	case string:
		result.Str = &d
	case float64:
		var s string
		if float64(int64(d)) == d {
			s = fmt.Sprintf("%d", int64(d))
		} else {
			s = fmt.Sprintf("%f", d)
		}
		result.Str = &s
	case bool:
		s := fmt.Sprintf("%t", d)
		result.Str = &s
	default:
		panic(fmt.Sprintf("don't know how to parse %v of type %T", data, data))
	}
	return &result
}

func extractUrls(baseUrl string, m *jsonValue) []string {
	var result []string
	switch true {
	case m.Map != nil:
		for key, val := range m.Map {
			if key == "href" {
				url := *val.Str
				if strings.Contains(url, "github.com") {
					continue
				}
				url = url[len(baseUrl)+1:]
				result = append(result, url)
			} else {
				result = append(result, extractUrls(baseUrl, val)...)
			}
		}
	case m.Slice != nil:
		for _, val := range m.Slice {
			result = append(result, extractUrls(baseUrl, val)...)
		}
	}
	return result
}

type ComparisonFailure struct {
	field string
	note  string
}

func compare(response1, response2 *jsonValue, relativeUrl string) *ComparisonFailure {
	return compareInternal(response1, response2, "", true)
}

func compareInternal(response1, response2 *jsonValue, field string, root bool) *ComparisonFailure {
	// fmt.Println(field)
	if ignoredFields[field] {
		return nil
	}
	switch true {
	case response1.Map != nil:
		if response2.Map != nil {
			return compareMaps(response1.Map, response2.Map, field)
		}
		if response2.Slice != nil && root {
			return compareMapAndSlice(response1.Map, response2.Slice, field)
		}
		return &ComparisonFailure{
			note: "lhs has type map but rhs does not",
		}
	case response1.Slice != nil:
		if response2.Slice != nil {
			err := compareSlices(response1.Slice, response2.Slice, field, false)
			if err != nil {
				err = compareSlices(response1.Slice, response2.Slice, field, true)
			}
			return err
		}
		if response2.Map != nil && root {
			return compareMapAndSlice(response2.Map, response1.Slice, field)
		}
		return &ComparisonFailure{
			note: "lhs has type slice but rhs does not",
		}
	case response1.Str != nil:
		if response2.Str != nil {
			if *response1.Str == *response2.Str {
				return nil
			}
			return &ComparisonFailure{
				note: fmt.Sprintf("string(%s) != string(%s)", *response1.Str, *response2.Str),
			}
		}
		return &ComparisonFailure{
			note: "lhs has type string but rhs does not",
		}
	case response1.Float64 != nil:
		if response2.Float64 != nil {
			if *response1.Float64 == *response2.Float64 {
				return nil
			}
			return &ComparisonFailure{
				note: fmt.Sprintf("float64(%f) != float64(%f)", *response1.Float64, *response2.Float64),
			}
		}
		return &ComparisonFailure{
			note: "lhs has type float64 but rhs does not",
		}
	default:
		panic(fmt.Sprintf("don't know how to compare values\n1=%+v\n2=%+v", response1, response2))
	}
}

func compareMapAndSlice(m map[string]*jsonValue, s []*jsonValue, field string) *ComparisonFailure {
	if len(m) != 1 {
		return &ComparisonFailure{
			note: "lhs has type map but rhs has type slice",
		}
	}
	var uniqueMapValue *jsonValue
	for _, uniqueMapValue = range m {
	}
	if uniqueMapValue.Slice == nil {
		return &ComparisonFailure{
			note: "lhs has type map but rhs has type slice",
		}
	}
	err := compareSlices(uniqueMapValue.Slice, s, field, false)
	if err != nil {
		err = compareSlices(uniqueMapValue.Slice, s, field, true)
	}
	return err
}

func compareSlices(lhs, rhs []*jsonValue, field string, sort bool) *ComparisonFailure {
	if len(lhs) != len(rhs) {
		return &ComparisonFailure{
			note: fmt.Sprintf("slices do not have the same length: %d != %d", len(lhs), len(rhs)),
		}
	}
	if sort {
		sortSlice(lhs)
		sortSlice(rhs)
	}
	for i := 0; i < len(lhs); i++ {
		if err := compareInternal(lhs[i], rhs[i], fmt.Sprintf("%s[%d]", field, i), false); err != nil {
			fmt.Printf("Fails\n%s\n!=\n%s\n", lhs[i], rhs[i])
			err.field = fmt.Sprintf("[%d]%s", i, err.field)
			return err
		}
	}
	return nil
}

func sortSlice(s []*jsonValue) {
	sort.Slice(s, func(i, j int) bool {
		return s[i].String() < s[j].String()
	})
}

func compareMaps(lhs, rhs map[string]*jsonValue, field string) *ComparisonFailure {
	for key, lhsVal := range lhs {
		if ignoredFields[key] {
			continue
		}
		rhsVal, ok := rhs[key]
		// If the lhs is an empty slice and rhs is nil, that's fine
		if !ok && lhsVal.Slice != nil && len(lhsVal.Slice) == 0 {
			continue
		}
		if !ok && !ignoredFields[key] {
			rhsKeys := make([]string, 0, len(rhs))
			for k := range rhs {
				rhsKeys = append(rhsKeys, k)
			}
			return &ComparisonFailure{
				field: key,
				note:  fmt.Sprintf("rhs is missing this field; lhs value=%+v\nrhs has keys: %v", lhsVal, rhsKeys),
			}
		}
		if key == "href" && compareHost(*lhsVal.Str, *rhsVal.Str) {
			continue
		}
		newField := key
		if field != "" {
			newField = field + "." + key
		}
		if err := compareInternal(lhsVal, rhsVal, newField, false); err != nil {
			if err.field == "" {
				err.field = key
			} else {
				err.field = fmt.Sprintf("%s.%s", key, err.field)
			}
			return err
		}
	}
	for key, rhsVal := range rhs {
		_, ok := lhs[key]
		if ok {
			continue
		}
		if rhsVal.Map != nil && len(rhsVal.Map) == 0 {
			continue
		}
		// If the rhs is an empty slice and lhs is nil, that's fine
		if rhsVal.Slice != nil && len(rhsVal.Slice) == 0 {
			continue
		}
		if rhsVal.Str != nil && *rhsVal.Str == "" {
			continue
		}
		if ignoredFields[key] {
			continue
		}
		return &ComparisonFailure{
			field: key,
			note:  fmt.Sprintf("lhs is missing this value; rhs value=%+v", rhsVal),
		}

	}
	return nil
}

func compareHost(lhs, rhs string) bool {
	lhsP, err := url.Parse(lhs)
	if err != nil {
		return false
	}
	rhsP, err := url.Parse(rhs)
	if err != nil {
		return false
	}
	return lhsP.Path == rhsP.Path
}

func snakeCaseToCamelCase(snakeCase string) (camelCase string) {
	lastCharWasUnderscore := false
	for _, c := range snakeCase {
		switch true {
		case c == '_':
			lastCharWasUnderscore = true
		case lastCharWasUnderscore:
			camelCase += strings.ToUpper(string(c))
			lastCharWasUnderscore = false
		default:
			camelCase += string(c)
		}
	}
	return
}
