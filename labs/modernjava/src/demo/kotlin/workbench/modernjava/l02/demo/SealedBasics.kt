package workbench.modernjava.l02.demo

import java.lang.reflect.Modifier

// Kotlin has no permits clause: the direct subtypes are the ones declared in this package and module
sealed interface Command {
    data class Authorize(val authCode: String, val amountMinor: Long) : Command   // final by default
    data object Capture : Command
    data class Refund(val amountMinor: Long) : Command
}

// Step 2: uncomment this line and compile. Then try it in another package.
// class Void : Command

/** kotlinc writes the same PermittedSubclasses attribute that javac does. */
fun main() {
    println("Command.isSealed():  ${Command::class.java.isSealed}")
    for (c in Command::class.java.permittedSubclasses) {
        println("permits:             ${c.simpleName}" + if (Modifier.isFinal(c.modifiers)) " (final)" else "")
    }
    println("Refund.isSealed():   ${Command.Refund::class.java.isSealed}")
}
