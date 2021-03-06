
package main

import (
    "fmt"
	"log"
    "os"

    "github.com/dgraph-io/badger"
)

func main () {

    //ref: <https://github.com/dgraph-io/badger#opening-a-database> and
    //<https://github.com/dgraph-io/badger#iterating-over-keys>
	// Open the Badger database located in the /tmp/badger directory.
	// It will be created if it doesn't exist.
    if (len(os.Args) < 2) {
        return
    }
	opts := badger.DefaultOptions
    dbPath := os.Args[1]
	opts.Dir = dbPath
	opts.ValueDir = dbPath
	db, err := badger.Open(opts)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	err = db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.PrefetchSize = 10
		it := txn.NewIterator(opts)
		for it.Rewind(); it.Valid(); it.Next() {
			item := it.Item()
			k := item.Key()
			v, err := item.Value()
			if err != nil {
				return err
			}
			fmt.Printf("key=%s, value=%s\n", k, v)
		}
		return nil
	})
}
