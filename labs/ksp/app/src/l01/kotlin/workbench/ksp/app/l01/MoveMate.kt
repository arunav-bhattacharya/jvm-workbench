package workbench.ksp.app.l01

import workbench.ksp.annotations.Inventory

// Lesson 1, the real build. Nobody wrote a card for these classes. Before the Kotlin compiler runs, KSP runs a
// ready-made card processor (lesson 2's, named in labs/ksp/app/src/l01/processors.txt), and it writes one new
// file per class into labs/ksp/app/build/generated/ksp/l01/kotlin/workbench/ksp/app/l01/.
//   ./gradlew :ksp:app:kspL01Kotlin                                    run KSP alone, then open that folder
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l01.MoveMateKt     compile everything and print the cards

@Inventory
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

@Inventory
data class Lamp(val name: String, val bulbs: Int, val shade: String?)

@Inventory
class Bookshelf(val shelves: Int, val books: List<String>)

@Inventory
data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)

fun main() {
    // inventoryCard() is defined nowhere in src/l01: KSP generated it during this build
    println(Box("kitchen 1", "kitchen", 5200, fragile = true).inventoryCard())
    println(Lamp("desk lamp", 1, null).inventoryCard())
    println(Bookshelf(3, listOf("atlas", "cookbook")).inventoryCard())
    println(Plant("fern", 2.5).inventoryCard())
}
