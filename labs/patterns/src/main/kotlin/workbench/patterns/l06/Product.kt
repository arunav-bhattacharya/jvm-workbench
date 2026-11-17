package workbench.patterns.l06

import java.util.concurrent.atomic.AtomicInteger

/**
 * One product from the shop's catalog: its code and its name. Thousands of order lines name one of a
 * few hundred products, so the program keeps ONE instance per code and shares it: a flyweight. The
 * constructor is private, so [of] is the only way in.
 *
 * Rules for [of]:
 *  - the same code always returns the same instance (`===`), from any thread;
 *  - an unknown code throws IllegalArgumentException("unknown product: <code>");
 *  - the constructor runs at most once per code, even when eight threads ask for a new code at once.
 */
class Product private constructor(val code: String, val name: String) {
    init {
        created.incrementAndGet()          // counts constructor runs; the tests read it
    }

    override fun toString() = "$code $name"

    companion object {
        private val created = AtomicInteger()

        /** How many instances have been built since the JVM started. */
        val instancesCreated: Int get() = created.get()

        /** The shop's catalog. Given; don't change it. */
        val CATALOG: Map<String, String> = mapOf(
            "T-1001" to "Breakfast tea",
            "J-2001" to "Strawberry jam",
            "B-3001" to "Rye bread",
            "C-4001" to "Coffee beans",
        )

        /** The one shared instance for [code]. Keep a pool in this companion object. */
        fun of(code: String): Product =
            TODO("look up the name, then return the pooled instance, building it at most once")
    }
}
