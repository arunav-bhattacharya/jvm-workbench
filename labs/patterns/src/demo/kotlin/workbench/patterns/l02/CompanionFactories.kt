package workbench.patterns.l02

// Three Kotlin factory shapes, and a factory that returns a sealed result instead of throwing.

class Iban private constructor(val country: String, val digits: String) {
    override fun toString() = "$country****${digits.takeLast(4)}"

    companion object {
        // 1. a named factory in the companion: Iban.parse("...")
        fun parse(raw: String): IbanResult {
            val s = raw.replace(" ", "").uppercase()
            return when {
                s.length < 15 -> IbanResult.TooShort(s.length)
                !s.take(2).all(Char::isLetter) -> IbanResult.BadCountry(s.take(2))
                else -> IbanResult.Ok(Iban(s.take(2), s.drop(2)))
            }
        }
    }
}

sealed interface IbanResult {
    data class Ok(val iban: Iban) : IbanResult
    data class TooShort(val length: Int) : IbanResult
    data class BadCountry(val prefix: String) : IbanResult
}

class Fee private constructor(val bps: Int) {
    override fun toString() = "Fee($bps bps)"

    companion object {
        private val standard = Fee(290)
        // 2. operator invoke: callers write Fee(290) and get the cached instance
        operator fun invoke(bps: Int): Fee = if (bps == 290) standard else Fee(bps)
    }
}

interface Ledger { fun post(entry: String) }

// 3. a top-level function named like the interface, as kotlinx.coroutines does with Job() and CoroutineScope()
fun Ledger(): Ledger = object : Ledger {
    override fun post(entry: String) = println("  ledger <- $entry")
}

fun describe(r: IbanResult): String = when (r) {      // no else: the compiler checks every case is here
    is IbanResult.Ok -> "ok: ${r.iban}"
    is IbanResult.TooShort -> "too short (${r.length} chars)"
    is IbanResult.BadCountry -> "bad country code '${r.prefix}'"
}

fun main() {
    listOf("DE89 3704 0044 0532 0130 00", "DE89 3704", "12345678901234567890").forEach {
        println("parse(\"$it\") -> ${describe(Iban.parse(it))}")
    }
    println("Fee(290) === Fee(290)? ${Fee(290) === Fee(290)}")
    println("Fee(150) === Fee(150)? ${Fee(150) === Fee(150)}")
    Ledger().post("fee 29.00 EUR")
}
