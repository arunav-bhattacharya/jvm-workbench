package workbench.ksp.app.l05

import workbench.ksp.annotations.Builder

// Lesson 5: the same MoveMate classes as lesson 4, run through the builder processor with checks.
// Box and Plant have default values, so the build prints one warning for each (and still writes their builders).

@Builder
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

@Builder
data class Lamp(val name: String, val bulbs: Int, val shade: String?)

@Builder
class Bookshelf(val shelves: Int, val books: List<String>)

@Builder
data class Plant(
    val kind: String,
    val potLitres: Double,
    val waterEveryDays: Int = 7,
)
