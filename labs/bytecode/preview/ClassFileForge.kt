// JDK 24 or later, with kotlinc running on that JDK. From labs/:
//   kotlinc bytecode/preview/ClassFileForge.kt -jvm-target 21 -include-runtime -d build/cfforge.jar
//   java -jar build/cfforge.jar
// Builds a class from scratch, verifies a broken one, then transforms the first.

import java.lang.classfile.ClassFile
import java.lang.classfile.ClassTransform
import java.lang.classfile.CodeTransform
import java.lang.classfile.MethodModel
import java.lang.classfile.instruction.ConstantInstruction
import java.lang.constant.ClassDesc
import java.lang.constant.ConstantDescs.CD_String
import java.lang.constant.ConstantDescs.CD_int
import java.lang.constant.ConstantDescs.CD_long
import java.lang.constant.ConstantDescs.CD_void
import java.lang.constant.MethodTypeDesc
import java.lang.invoke.MethodHandles

fun main() {
    val cf = ClassFile.of()
    val static = ClassFile.ACC_PUBLIC or ClassFile.ACC_STATIC

    // 1. build: a class with seconds(long steps) = steps * 32 / 1_000 and a debug method
    val fade = cf.build(ClassDesc.of("Fade")) { clb ->
        clb.withFlags(ClassFile.ACC_PUBLIC or ClassFile.ACC_FINAL)
        clb.withMethodBody("seconds", MethodTypeDesc.of(CD_long, CD_long), static) { cob ->
            cob.lload(0)                  // push the number of steps (slots 0 and 1)
                .loadConstant(32L)        // push the length of one step, in milliseconds (ldc2_w)
                .lmul()
                .loadConstant(1_000L)
                .ldiv()
                .lreturn()
        }
        clb.withMethodBody("debugTrace", MethodTypeDesc.of(CD_void, CD_String), static) { cob -> cob.return_() }
    }
    println("built Fade: ${fade.size} bytes, verify errors ${cf.verify(fade)}")
    val c1 = MethodHandles.lookup().defineClass(fade)
    println("Fade.seconds(12500) = ${c1.getMethod("seconds", Long::class.javaPrimitiveType).invoke(null, 12_500L)}")

    // 2. verify before you load: an int method that returns a String
    val broken = cf.build(ClassDesc.of("Broken")) { clb ->
        clb.withMethodBody("answer", MethodTypeDesc.of(CD_int), static) { cob ->
            // Kotlin's String type doesn't expose Java's ConstantDesc, so pass a constant-pool entry
            cob.ldc(cob.constantPool().stringEntry("forty-two")).ireturn()
        }
    }
    println("verify(Broken): ${cf.verify(broken)}")

    // 3. transform: drop debug methods and change the 32 constant to 40, as a new class FadeV2
    val slower = CodeTransform { cob, element ->
        if (element is ConstantInstruction && element.constantValue().equals(32L)) {
            cob.loadConstant(40L)         // replace this element
        } else {
            cob.with(element)             // pass everything else through unchanged
        }
    }
    val transform = ClassTransform
        .dropping { it is MethodModel && it.methodName().stringValue().startsWith("debug") }
        .andThen(ClassTransform.transformingMethodBodies(slower))
    val v2 = cf.transformClass(cf.parse(fade), ClassDesc.of("FadeV2"), transform)
    val c2 = MethodHandles.lookup().defineClass(v2)
    println("FadeV2 methods ${cf.parse(v2).methods().map { it.methodName().stringValue() }}, " +
        "seconds(12500) = ${c2.getMethod("seconds", Long::class.javaPrimitiveType).invoke(null, 12_500L)}")
}
