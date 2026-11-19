package workbench.ksp.app.l06

// Lesson 6, Try it in the real build: receipts from round 1 and 2, cards from rounds 1 to 3.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l06.MovingDayKt
fun main() {
    val lampReceipt = Lamp("desk lamp", 1, null).receipt(signedBy = "Ana")
    val vanReceipt = Van("MV-1", lastLoad = lampReceipt).receipt(signedBy = "Ben")

    println(Box("plates", "kitchen", 4200, fragile = true).inventoryCard())
    println(lampReceipt.inventoryCard())
    println(vanReceipt.inventoryCard())
}
