package workbench.ksp.app.l02

import workbench.ksp.annotations.Inventory

// Lesson 2, the real build: your @Inventory processor (with -Pmine=l02) or the reference one runs on this file.
//   ./gradlew :ksp:app:kspL02Kotlin -Pmine=l02          run KSP alone with yours; it works even on the stub
//   then open labs/ksp/app/build/generated/ksp/l02/kotlin/workbench/ksp/app/l02/LampInventoryCard.kt
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l02.MovingDayKt -Pmine=l02     once your lab passes

@Inventory
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

@Inventory
data class Lamp(val name: String, val bulbs: Int, val shade: String?)

@Inventory
class Bookshelf(val shelves: Int, val books: List<String>)

@Inventory
data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)

fun main() {
    val van = listOf(
        Box("kitchen 1", "kitchen", 5200, fragile = true).inventoryCard(),
        Lamp("desk lamp", 1, null).inventoryCard(),
        Bookshelf(3, listOf("atlas", "cookbook")).inventoryCard(),
        Plant("fern", 2.5).inventoryCard(),
    )
    van.forEach(::println)
}
