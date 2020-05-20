# Vendorizing GTFS Realtime

1. rename the gtfs realtime proto file

1. Change the package name inside 

1. In any extensions, change the reference to the right proto file and also the package

1. Run
```
protoc --python_out=. --proto_path=. *.proto
```

1. Change the Python import reference in the extension