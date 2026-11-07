package workbench.bytecode.l02

import java.lang.reflect.Modifier

// Five Kotlin shapes. main() prints the JVM members of each class, close to what `javap -p` shows.

data class Payment(val id: String, val amountMinor: Long = 0)

class Account(val owner: String) {
    var balanceMinor: Long = 0
        private set                               // a getter, and no setter at all
    val isEmpty: Boolean get() = balanceMinor == 0L
    lateinit var iban: String                     // a public field, plus getter and setter

    companion object {
        const val MAX_MINOR = 10_000_000L         // public static final on Account
        val DEFAULT_CURRENCY = "EUR"              // private static on Account, getter on Companion
        @JvmStatic fun open(owner: String) = Account(owner)   // static on Account AND on Companion
        fun create(owner: String) = Account(owner)            // only on Companion
    }
}

object Registry {
    val accounts = mutableListOf<Account>()
}

fun greet(name: String = "Ana", punct: Char = '!') = "Hello $name$punct"

fun main() {
    val classes = listOf(
        Payment::class.java, Account::class.java, Account.Companion::class.java,
        Registry::class.java, Class.forName("workbench.bytecode.l02.KotlinShapesKt"),
    )
    for (c in classes) {
        println("${Modifier.toString(c.modifiers)} class ${c.name}")
        c.declaredFields.sortedBy { it.name }.forEach {
            println("    field  ${Modifier.toString(it.modifiers)} ${it.type.simpleName} ${it.name}")
        }
        c.declaredConstructors.forEach { k ->
            println("    ctor   (${k.parameterTypes.joinToString { it.simpleName }})" + if (k.isSynthetic) " synthetic" else "")
        }
        c.declaredMethods.sortedBy { it.name }.forEach { m ->
            println("    method ${Modifier.toString(m.modifiers)} ${m.name}(${m.parameterTypes.joinToString { it.simpleName }})")
        }
    }
}
