package workbench.patterns.l03

// Two traps in data class copy(): it is shallow, and it ignores a private constructor.

data class Cart(val id: String, val skus: MutableList<String>)

data class Email private constructor(val value: String) {
    companion object {
        fun of(raw: String): Email {
            require("@" in raw) { "not an email: $raw" }
            return Email(raw)
        }
    }
}

data class Amount(val minor: Long) {
    init { require(minor >= 0) { "negative amount: $minor" } }
}

fun main() {
    // trap 1: copy() copies the reference to the list, not the list
    val c1 = Cart("c1", mutableListOf("sku-1"))
    val c2 = c1.copy(id = "c2")
    c2.skus += "sku-2"
    println("c1.skus after changing c2: ${c1.skus}")

    // trap 2: the private constructor does not cover the generated copy()
    val email = Email.of("anna@example.com")
    val broken = email.copy(value = "not-an-email")
    println("copy() skipped the factory: $broken")

    // init blocks DO run on copy()
    val result = runCatching { Amount(5).copy(minor = -1) }
    println("Amount(5).copy(minor = -1): ${result.exceptionOrNull()?.message}")
}
