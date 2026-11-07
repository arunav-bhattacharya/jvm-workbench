package workbench.modernjava.l04.demo

data class MoneyAmount(val minor: Long, val currency: String)

// Kotlin's value class today: one property, erased to that property wherever the compiler can
@JvmInline
value class Iban(val value: String)

fun describeIban(iban: Iban): String = "IBAN ending ${iban.value.takeLast(4)}"

/** Data classes are identity objects today; @JvmInline value classes are a compile-time trick. */
fun main() {
    val a = MoneyAmount(4_200, "EUR")
    val b = MoneyAmount(4_200, "EUR")

    println("==: ${a == b}, ===: ${a === b}")
    synchronized(a) {
        println("synchronized on a data class: allowed, because it has an identity")
    }

    val iban = Iban("DE89370400440532013000")
    println(describeIban(iban))                                   // compiled to a call taking a plain String
    val asAny: Any = iban                                         // used as another type: boxed
    println("as Any, the object is a ${asAny::class.java.simpleName}")
    val inList = listOf(iban)                                     // used as a generic T: boxed
    println("in a List, the element is a ${(inList[0] as Any)::class.java.simpleName}")
}
