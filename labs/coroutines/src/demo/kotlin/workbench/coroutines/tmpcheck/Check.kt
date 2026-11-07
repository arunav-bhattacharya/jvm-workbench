package workbench.coroutines.tmpcheck

private fun checksum(i: Long): Long {
    var x = i
    repeat(20) {
        x = x xor (x ushr 33)
        x *= -0xae502812aa7333L
        x = x xor (x ushr 29)
    }
    return x
}
@Volatile var sink = 0L
fun main() {
    repeat(3) {
        val t = System.nanoTime()
        var sum = 0L
        for (i in 0 until 10_000_000L) sum += checksum(i)
        sink = sum
        println("full loop ${(System.nanoTime() - t) / 1_000_000} ms")
    }
}
