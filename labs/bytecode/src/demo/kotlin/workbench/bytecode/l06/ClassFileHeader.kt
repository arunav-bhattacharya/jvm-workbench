package workbench.bytecode.l06

import java.io.ByteArrayInputStream
import java.io.DataInputStream
import java.util.HexFormat

/** A Kotlin class for the Java twin to read. */
class HeaderMarker

/** The first ten bytes of three class files: magic, version and constant pool size. */
fun main() {
    show(HeaderMarker::class.java)   // compiled by kotlinc in the labs build with jvmTarget 21
    show(Unit::class.java)           // the Kotlin standard library jar
    show(Any::class.java)            // java.lang.Object, from the JDK you are running
}

private fun show(c: Class<*>) {
    val bytes = c.getResourceAsStream(c.simpleName + ".class")!!.use { it.readAllBytes() }
    val input = DataInputStream(ByteArrayInputStream(bytes))
    val magic = input.readInt()                // u4
    val minor = input.readUnsignedShort()      // u2
    val major = input.readUnsignedShort()      // u2
    val poolCount = input.readUnsignedShort()  // u2: entries are numbered 1 .. poolCount - 1
    println("%-34s %s  magic=%X  version=%d.%d (Java %d)  pool entries=%d  size=%d bytes".format(
        c.name, HexFormat.ofDelimiter(" ").formatHex(bytes, 0, 10),
        magic, major, minor, major - 44, poolCount - 1, bytes.size))
}
