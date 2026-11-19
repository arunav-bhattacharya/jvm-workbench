package workbench.ksp.app.l09

import workbench.ksp.annotations.Inventory
import workbench.ksp.annotations.Room

// Lesson 9's boxes. Two processors read them in this build: the packing slip (lesson 9's port of a javac
// processor) and lesson 7's cards and master list (named in processors.txt).
@Inventory
@Room("hall")
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

@Inventory
@Room("living room")
data class Lamp(val name: String, val bulbs: Int, val shade: String?)

@Inventory
@Room("study")
class Bookshelf(val shelves: Int, val books: List<String>)

@Inventory
data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)

/** The four things the timing demo makes cards for. */
fun movingDayThings(): List<Any> = listOf(
    Box("books", "study", 12_000),
    Lamp("desk lamp", 1, null),
    Bookshelf(3, listOf("Dune", "Emma")),
    Plant("fern", 2.5),
)
