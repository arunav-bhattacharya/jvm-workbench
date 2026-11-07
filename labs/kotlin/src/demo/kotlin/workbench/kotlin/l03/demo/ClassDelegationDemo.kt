package workbench.kotlin.l03.demo

interface FeePolicy {
    fun feeMinor(amountMinor: Long): Long
}

class FlatFee(private val fee: Long) : FeePolicy {
    override fun feeMinor(amountMinor: Long): Long = fee
    override fun toString(): String = "FlatFee($fee)"
}

/** `by policy` forwards to the object passed in at construction, stored in a hidden final field. */
class ConfigurableFees(var policy: FeePolicy) : FeePolicy by policy

/** Delegating a Set forwards Set's methods, but not equals, hashCode or toString. */
class Tags(private val inner: MutableSet<String> = HashSet()) : MutableSet<String> by inner

fun main() {
    val fees = ConfigurableFees(FlatFee(25))
    println("fee: ${fees.feeMinor(10_000)}")
    fees.policy = FlatFee(99)                         // swap the policy...
    println("after swap, policy = ${fees.policy}, fee: ${fees.feeMinor(10_000)}")

    val a = Tags().apply { add("refund"); add("manual") }
    val b = Tags().apply { add("refund"); add("manual") }
    println("a = $a")
    println("a == b: ${a == b}, a.size = ${a.size}, \"refund\" in a: ${"refund" in a}")
}
