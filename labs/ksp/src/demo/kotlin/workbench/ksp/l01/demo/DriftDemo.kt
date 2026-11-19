package workbench.ksp.l01.demo

// MoveMate's lamps now record how many watts they draw, so Lamp gained a property. Nobody remembered the
// hand-written card, which was written before watts existed. Predict what the two lines print.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l01.demo.DriftDemoKt

data class Lamp(val name: String, val bulbs: Int, val shade: String?, val watts: Int)

// the card, exactly as it was written for the old Lamp
fun Lamp.inventoryCard(): String =
    "Lamp: name=$name, bulbs=$bulbs, shade=$shade"

fun main() {
    val lamp = Lamp("desk lamp", 1, null, 40)
    println("the lamp: $lamp")
    println("its card: ${lamp.inventoryCard()}")
}
