package workbench.ksp.app.l08

// Calls the generated builders and cards, the way the lesson's tests do through the bench.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l08.PackingKt
fun main() {
    val lamp = LampBuilder().name("desk lamp").bulbs(1).shade(null).build()
    val shelf = BookshelfBuilder().shelves(3).books(listOf("Dune", "Emma")).build()
    println(lamp.inventoryCard())
    println(shelf.inventoryCard())
}
