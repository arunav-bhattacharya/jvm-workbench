package workbench.generics.l01.demo

/** A settings box that holds Any. It compiles fine, and it fails far away from the bug. */
class AnyBox(var value: Any)

// "module A": sets up the merchant's settlement currency
fun configure(box: AnyBox) {
    box.value = 978                       // the bug: the ISO numeric code instead of "EUR"
}

// "module B": reads the setting much later, in another class, maybe another team's code
fun currencyLabel(box: AnyBox): String {
    val code = box.value as String        // the cast fails HERE, not where 978 went in
    return "Settles in $code"
}

fun main() {
    val box = AnyBox("EUR")
    configure(box)
    println("configure() returned. Nothing has failed yet.")
    try {
        println(currencyLabel(box))
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message}")
        println("thrown in: ${e.stackTrace.first()}")
    }
}
