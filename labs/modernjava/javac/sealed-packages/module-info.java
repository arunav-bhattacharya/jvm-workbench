// A named module: inside one module, a sealed type's subtypes may sit in other packages.
module pay {
    exports pay.api;
    exports pay.card;
}
