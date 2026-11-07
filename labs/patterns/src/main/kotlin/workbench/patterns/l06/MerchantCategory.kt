package workbench.patterns.l06

import java.util.concurrent.atomic.AtomicInteger

/**
 * A merchant category code (MCC) and its description. Millions of payments carry one of a few
 * hundred codes, so the system keeps ONE instance per code and shares it: a flyweight. The
 * constructor is private, so [of] is the only way in.
 *
 * Rules for [of]:
 *  - the same code always returns the same instance (`===`), from any thread;
 *  - an unknown code throws IllegalArgumentException("unknown MCC: <code>");
 *  - the constructor runs at most once per code, even when eight threads ask for a new code at once.
 */
class MerchantCategory private constructor(val code: String, val description: String) {
    init {
        created.incrementAndGet()          // counts constructor runs; the tests read it
    }

    override fun toString() = "$code $description"

    companion object {
        private val created = AtomicInteger()

        /** How many instances have been built since the JVM started. */
        val instancesCreated: Int get() = created.get()

        /** The codes this system knows. Given; don't change it. */
        val KNOWN: Map<String, String> = mapOf(
            "4111" to "Commuter transport",
            "5411" to "Grocery stores, supermarkets",
            "5812" to "Restaurants",
            "5999" to "Miscellaneous retail",
        )

        /** The one shared instance for [code]. Keep a pool in this companion object. */
        fun of(code: String): MerchantCategory =
            TODO("look up the description, then return the pooled instance, building it at most once")
    }
}
