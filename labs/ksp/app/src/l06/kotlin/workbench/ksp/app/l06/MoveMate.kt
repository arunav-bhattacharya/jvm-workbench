package workbench.ksp.app.l06

import workbench.ksp.annotations.Inventory
import workbench.ksp.annotations.Moving

// Lesson 6: two processors, several rounds. Watch them with `./gradlew :ksp:app:kspL06Kotlin`:
// round 1 writes LampReceipt and the card for Box, and sets Van aside; round 2 writes VanReceipt and LampReceipt's
// card; round 3 writes VanReceipt's card; round 4 writes nothing, so processing ends.

@Moving
data class Lamp(val name: String, val bulbs: Int, val shade: String?)

@Inventory
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

// LampReceipt is generated in round 1, so Van can't be read until round 2
@Moving
data class Van(val plate: String, val lastLoad: LampReceipt)
