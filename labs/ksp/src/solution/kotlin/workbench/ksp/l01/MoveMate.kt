package workbench.ksp.l01

import workbench.ksp.annotations.Inventory

// Given code: MoveMate, a small app that helps a family move house, and the four kinds of thing it moves.
// Each class carries the sticky note @Inventory: "make an inventory card for this one".

@Inventory
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

@Inventory
data class Lamp(val name: String, val bulbs: Int, val shade: String?)

@Inventory
class Bookshelf(val shelves: Int, val books: List<String>)

@Inventory
data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)
