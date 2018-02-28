
package kvwrapper

import (
	"log"
    "github.com/dgraph-io/badger"
)

//The public function must Start with Upper case, otherwise
//# command-line-arguments
//./parse_markdown.go:42:13: cannot refer to unexported name kvwrapper.writeToBadgerIO
//./parse_markdown.go:42:13: undefined: kvwrapper.writeToBadgerIO
//./parse_markdown.go:66:5: cannot refer to unexported name kvwrapper.writeToBadgerIO
//./parse_markdown.go:66:5: undefined: kvwrapper.writeToBadgerIO
func WriteToBadgerIO(key string, value string) {

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
    txn.Set([]byte(key), []byte(value))
    txn.Commit(nil)
}