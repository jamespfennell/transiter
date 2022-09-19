package main

import (
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"sync"
)

func main() {
	addr := flag.String("addr", "0.0.0.0:8090", "address to bind the source server on")
	debug := flag.Bool("debug", false, "enable debug logging")
	flag.Parse()

	pathToContent := concurrentMap{
		v: map[string]string{},
	}
	idGenerator := idGenerator{}
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if *debug {
			fmt.Println(r.Method, r.URL.Path)
		}
		if r.URL.Path == "/" {
			switch r.Method {
			case "GET":
				io.WriteString(w, strings.Join(pathToContent.Keys(), "\n"))
			case "POST":
				io.WriteString(w, idGenerator.Generate())
			default:
				w.WriteHeader(http.StatusMethodNotAllowed)
			}
		} else {
			switch r.Method {
			case "GET":
				content, ok := pathToContent.Get(r.URL.Path)
				if !ok {
					w.WriteHeader(http.StatusNotFound)
					return
				}
				io.WriteString(w, content)
			case "PUT":
				b, err := io.ReadAll(r.Body)
				if err != nil {
					w.WriteHeader(http.StatusInternalServerError)
					return
				}
				pathToContent.Set(r.URL.Path, string(b))
				w.WriteHeader(http.StatusOK)
			case "DELETE":
				if pathToContent.Delete(r.URL.Path) {
					w.WriteHeader(http.StatusOK)
				} else {
					w.WriteHeader(http.StatusNotFound)
				}
			default:
				w.WriteHeader(http.StatusMethodNotAllowed)
			}
		}
	})
	log.Printf("Source server listening on %s\n", *addr)
	err := http.ListenAndServe(*addr, nil)
	log.Printf("Source server stopped: %s\n", err)
}

type concurrentMap struct {
	m sync.RWMutex
	v map[string]string
}

func (m *concurrentMap) Set(key, value string) {
	m.m.Lock()
	defer m.m.Unlock()
	m.v[key] = value
}

func (m *concurrentMap) Get(key string) (string, bool) {
	m.m.RLock()
	defer m.m.RUnlock()
	value, ok := m.v[key]
	return value, ok
}

func (m *concurrentMap) Keys() []string {
	m.m.RLock()
	defer m.m.RUnlock()
	var keys []string
	for key := range m.v {
		keys = append(keys, key)
	}
	return keys
}

func (m *concurrentMap) Delete(key string) bool {
	m.m.Lock()
	defer m.m.Unlock()
	_, ok := m.v[key]
	delete(m.v, key)
	return ok
}

type idGenerator struct {
	m sync.Mutex
	i uint64
}

func (g *idGenerator) Generate() string {
	g.m.Lock()
	defer g.m.Unlock()
	g.i++
	return fmt.Sprintf("%x", g.i)
}
