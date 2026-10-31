package workbench.patterns.l02

enum class Network { VISA, MASTERCARD }

class Card private constructor(val network: Network, val last4: String) {
    override fun toString() = "$network ****$last4"

    companion object {
        // the only way to make a Card: every Card that exists passed these checks
        fun parse(raw: String): CardResult {
            val digits = raw.replace(" ", "")
            if (!digits.all { it in '0'..'9' }) return CardResult.Invalid("digits only")   // 1. shape
            if (digits.length !in 12..19) return CardResult.Invalid("length")             // 2. length
            if (!luhnOk(digits)) return CardResult.Invalid("checksum")                    // 3. checksum
            val network = networkOf(digits)                                               // 4. pick the product
                ?: return CardResult.Invalid("unsupported network")
            // inside the class the private constructor is visible; outside, nobody can call it
            return CardResult.Valid(Card(network, digits.takeLast(4)))
        }

        private fun networkOf(digits: String): Network? {
            val two = digits.take(2).toInt()
            val four = digits.take(4).toInt()
            return when {
                digits.startsWith("4") -> Network.VISA
                two in 51..55 || four in 2221..2720 -> Network.MASTERCARD
                else -> null
            }
        }
    }
}

sealed interface CardResult {
    data class Valid(val card: Card) : CardResult
    data class Invalid(val reason: String) : CardResult
}

fun luhnOk(digits: String): Boolean {
    var sum = 0
    digits.reversed().forEachIndexed { i, c ->
        var n = c - '0'
        if (i % 2 == 1) {
            n *= 2
            if (n > 9) n -= 9
        }
        sum += n
    }
    return sum % 10 == 0
}
