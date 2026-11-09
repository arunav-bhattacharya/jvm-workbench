package workbench.functional.l03.demo

import java.util.concurrent.ConcurrentHashMap

// A higher-order function that returns a function: same answers as f, but each one computed once.
fun <A : Any, R : Any> memoize(f: (A) -> R): (A) -> R {
    val cache = ConcurrentHashMap<A, R>()                 // captured: one cache per memoized function
    return { a -> cache.computeIfAbsent(a) { f(it) } }
}

// Pure but slow: imagine it scans a large BIN table on every call.
var binLookups = 0
fun issuerCountry(bin: String): String {
    binLookups++
    Thread.sleep(50)
    return if (bin.startsWith("4")) "NL" else "DE"
}

// Impure: the exchange rate moves while the service runs.
var eurUsd = 1.08
fun fxRate(pair: String): Double = if (pair == "EURUSD") eurUsd else 1.0

fun main() {
    val country = memoize(::issuerCountry)
    val bins = listOf("424242", "555555", "424242", "424242", "555555")
    val start = System.nanoTime()
    println(bins.map(country))
    println("lookups: $binLookups for ${bins.size} calls, %d ms".format((System.nanoTime() - start) / 1_000_000))

    val rate = memoize(::fxRate)
    println("EURUSD now:                    ${rate("EURUSD")}")
    eurUsd = 1.11                                         // the market moves
    println("EURUSD after the market moved: ${rate("EURUSD")}   (real rate: ${fxRate("EURUSD")})")
}
