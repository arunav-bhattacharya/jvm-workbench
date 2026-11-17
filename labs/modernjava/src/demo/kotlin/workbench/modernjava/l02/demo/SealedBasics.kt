package workbench.modernjava.l02.demo

import java.lang.reflect.Modifier

// Kotlin has no permits clause: the direct subtypes are the ones declared in this package and module
sealed interface Request {
    data class Borrow(val isbn: String, val days: Int) : Request   // final by default
    data class Renew(val extraDays: Int) : Request
    data object Return : Request
}

// Step 2: uncomment this line and compile. Then try it in another package.
// class Donate : Request

/** kotlinc writes the same PermittedSubclasses attribute that javac does. */
fun main() {
    println("Request.isSealed(): ${Request::class.java.isSealed}")
    for (c in Request::class.java.permittedSubclasses) {
        println("permits:            ${c.simpleName}" + if (Modifier.isFinal(c.modifiers)) " (final)" else "")
    }
    println("Renew.isSealed():   ${Request.Renew::class.java.isSealed}")
}
