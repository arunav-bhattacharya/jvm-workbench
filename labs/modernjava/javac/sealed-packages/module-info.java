// A named module: inside one module, a sealed type's subtypes may sit in other packages.
module library {
    exports library.api;
    exports library.book;
}
