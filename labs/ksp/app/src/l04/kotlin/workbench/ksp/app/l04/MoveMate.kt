package workbench.ksp.app.l04

import workbench.ksp.annotations.Builder

// Lesson 4: MoveMate's things, each with a sticky note asking for a builder.
// KSP writes the builders to labs/ksp/app/build/generated/ksp/l04/kotlin/workbench/ksp/app/l04/.

@Builder
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

@Builder
data class Lamp(val name: String, val bulbs: Int, val shade: String?)

@Builder
class Bookshelf(val shelves: Int, val books: List<String>)

@Builder
data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)
