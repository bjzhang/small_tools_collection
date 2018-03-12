
package kvwrapper

import (
	"log"
    "github.com/dgraph-io/badger"
)

type KeyvalueStore struct {
    db *badger.DB
}

    //open(dbFile string) err error
    //write(key string, value string)
//The public function must Start with Upper case, otherwise
//# command-line-arguments
//./parse_markdown.go:42:13: cannot refer to unexported name kvwrapper.writeToBadgerIO
//./parse_markdown.go:42:13: undefined: kvwrapper.writeToBadgerIO
//./parse_markdown.go:66:5: cannot refer to unexported name kvwrapper.writeToBadgerIO
//./parse_markdown.go:66:5: undefined: kvwrapper.writeToBadgerIO
func WriteToBadgerIO(db *badger.DB, key string, value string) {
    txn := db.NewTransaction(true)
    txn.Set([]byte(key), []byte(value))
    txn.Commit(nil)
}

func (kv *KeyvalueStore)OpenKV(dbPath string) {
	//ref: <https://github.com/dgraph-io/badger#opening-a-database>
	// Open the Badger database located in the /tmp/badger directory.
	// It will be created if it doesn't exist.
	opts := badger.DefaultOptions
	opts.Dir = dbPath
	opts.ValueDir = dbPath
	db, err := badger.Open(opts)
	if err != nil {
		log.Fatal(err)
	}
    kv.db = db
}

func (kv *KeyvalueStore)CloseKV() {
	kv.db.Close()
}

func (kv *KeyvalueStore)WriteKV(key string, value string) {
    WriteToBadgerIO(kv.db, key, value)
}

func (kv *KeyvalueStore)SetCompact(compact bool) {
    badger.StopCompact = compact
}
