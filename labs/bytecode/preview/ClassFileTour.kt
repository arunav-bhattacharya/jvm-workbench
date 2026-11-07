// JDK 24 or later, with kotlinc running on that JDK. From labs/:
//   kotlinc bytecode/preview/ClassFileTour.kt -jvm-target 21 -include-runtime -d build/cftour.jar
//   java -jar build/cftour.jar [path/to/Some.class]
// With no argument it reads StackDemo.class from lesson 2, or java.lang.Integer from the JDK.

import java.lang.classfile.ClassFile
import java.lang.classfile.instruction.InvokeInstruction
import java.nio.file.Files
import java.nio.file.Path

fun main(args: Array<String>) {
    val p = Path.of(args.firstOrNull() ?: "bytecode/build/classes/java/demo/workbench/bytecode/l02/StackDemo.class")
    val bytes = if (Files.exists(p)) Files.readAllBytes(p)
                else Int::class.javaObjectType.getResourceAsStream("Integer.class")!!.readAllBytes()

    // 1. parse: an immutable model, inflated lazily as you ask for parts
    val cm = ClassFile.of().parse(bytes)
    println("${cm.thisClass().asInternalName()} extends ${cm.superclass().map { it.asInternalName() }.orElse("-")}, major ${cm.majorVersion()}")

    // 2. the constant pool, counted by kind of entry
    val kinds = cm.constantPool().groupingBy { it.javaClass.interfaces[0].simpleName }.eachCount().toSortedMap()
    println("constant pool: $kinds")

    // 3. methods, and the invoke instructions inside each one
    for (m in cm.methods()) {
        val invokes = m.code().map { code -> code.elementStream().filter { it is InvokeInstruction }.count() }.orElse(0L)
        println("  ${m.methodName().stringValue()}${m.methodType().stringValue()}  invokes=$invokes")
    }
}
