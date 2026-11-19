package workbench.ksp.l01

// Part 1: do the helper's job by hand. A card is the class's simple name, a colon, then name=value for each
// primary constructor property, in the order they are declared, joined with ", ".

/** Given: `Box: label=kitchen 1, room=kitchen, weightGrams=5200, fragile=true`. */
fun Box.inventoryCard(): String =
    "Box: label=$label, room=$room, weightGrams=$weightGrams, fragile=$fragile"

/** Given: `Bookshelf: shelves=3, books=[atlas, cookbook]`. */
fun Bookshelf.inventoryCard(): String =
    "Bookshelf: shelves=$shelves, books=$books"

/** `Lamp: name=desk lamp, bulbs=1, shade=null`. */
fun Lamp.inventoryCard(): String =
    TODO("write Lamp's card by hand, in the same format as Box's")

/** `Plant: kind=fern, potLitres=2.5, waterEveryDays=7`. */
fun Plant.inventoryCard(): String =
    TODO("write Plant's card by hand, in the same format as Box's")
