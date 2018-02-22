
package main

import (
	"log"

    "github.com/dgraph-io/badger"
)

func main () {

	//ref: <https://github.com/dgraph-io/badger#opening-a-database>
	// Open the Badger database located in the /tmp/badger directory.
	// It will be created if it doesn't exist.
	opts := badger.DefaultOptions
	opts.Dir = "/tmp/badger"
	opts.ValueDir = "/tmp/badger"
	db, err := badger.Open(opts)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

    txn := db.NewTransaction(true)
    txn.Set([]byte("1"), []byte("1234"))
    txn.Commit(nil)
}
