package workbench.generics.l01.demo

/** A storeroom box that holds Any. It compiles fine, and it fails far away from the bug. */
class AnyBox(var value: Any)

// the back room: restocks the box before the shop opens
fun restock(box: AnyBox) {
    box.value = 12                          // the bug: how many apples, not which variety
}

// the counter: reads the box much later, in another part of the program
fun signFor(box: AnyBox): String {
    val variety = box.value as String       // the cast fails HERE, not where 12 went in
    return "Today's apple: $variety"
}

fun main() {
    val box = AnyBox("Gala")
    restock(box)
    println("restock() returned. Nothing has failed yet.")
    try {
        println(signFor(box))
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message}")
        println("thrown in: ${e.stackTrace.first()}")
    }
}
