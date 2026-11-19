package workbench.ksp.app.l07

// Prints the master list and one card per thing, through code KSP generated in this build:
// MovingDayList (aggregating) and the inventoryCard() functions (isolating).
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l07.MovingDayKt
//   ./gradlew :ksp:app:compileL07Kotlin -Pksp.incremental.log=true     then read build/kspCaches/l07/logs/
fun main() {
    val things = listOf(
        Box("books", "study", 12_000),
        Lamp("desk lamp", 1, null),
        Bookshelf(3, listOf("Dune", "Emma")),
        Plant("fern", 2.5),
    )
    println("MovingDayList: ${MovingDayList.names}")
    for (thing in things) println(MovingDayList.cardFor(thing))
}
