library(SRAdb)
if(!file.exists('/db/SRAmetadb.sqlite')) {
    getSRAdbFile(destdir='/db')
} else {
    print('DB file already exists')
}
