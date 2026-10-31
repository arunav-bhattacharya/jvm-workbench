package workbench.patterns.l02

enum class Network { VISA, MASTERCARD }

/**
 * A card number that passed validation. The constructor is private: the only way to get a
 * [Card] is the factory [Card.parse], so every [Card] in the system is a valid one.
 */
class Card private constructor(val network: Network, val last4: String) {
    override fun toString() = "$network ****$last4"

    companion object {
        /**
         * Parses a raw card number such as "4111 1111 1111 1111". Never throws: bad input comes
         * back as [CardResult.Invalid] with one of these reasons, checked in this order:
         *
         * 1. remove spaces; anything left that is not a digit: "digits only"
         * 2. fewer than 12 or more than 19 digits: "length"
         * 3. [luhnOk] fails: "checksum"
         * 4. the network comes from the prefix: "4" is VISA; "51" to "55", or a four-digit prefix
         *    from 2221 to 2720, is MASTERCARD; anything else: "unsupported network"
         *
         * A good number comes back as [CardResult.Valid] holding the card, its network and last four digits.
         */
        fun parse(raw: String): CardResult = TODO("validate in the order above, then pick the network from the prefix")
    }
}

/** What [Card.parse] returns. The caller's `when` must handle both cases, and the compiler checks it. */
sealed interface CardResult {
    data class Valid(val card: Card) : CardResult
    data class Invalid(val reason: String) : CardResult
}

/** The Luhn checksum every card number carries. Given; you don't need to change it. */
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
