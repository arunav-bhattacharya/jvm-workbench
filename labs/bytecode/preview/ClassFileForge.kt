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

    // 1. build: a class with fee(long) = amount * 290 / 10_000 and a debug method
    val feeRule = cf.build(ClassDesc.of("FeeRule")) { clb ->
        clb.withFlags(ClassFile.ACC_PUBLIC or ClassFile.ACC_FINAL)
        clb.withMethodBody("fee", MethodTypeDesc.of(CD_long, CD_long), static) { cob ->
            cob.lload(0)                  // push the amount (slots 0 and 1)
                .ldc(290L)                // push the rate in basis points
                .lmul()
                .ldc(10_000L)
                .ldiv()
                .lreturn()
        }
        clb.withMethodBody("debugTrace", MethodTypeDesc.of(CD_void, CD_String), static) { cob -> cob.return_() }
    }
    println("built FeeRule: ${feeRule.size} bytes, verify errors ${cf.verify(feeRule)}")
    val c1 = MethodHandles.lookup().defineClass(feeRule)
    println("FeeRule.fee(125000) = ${c1.getMethod("fee", Long::class.javaPrimitiveType).invoke(null, 125_000L)}")

    // 2. verify before you load: an int method that returns a String
    val broken = cf.build(ClassDesc.of("Broken")) { clb ->
        clb.withMethodBody("answer", MethodTypeDesc.of(CD_int), static) { cob -> cob.ldc("forty-two").ireturn() }
    }
    println("verify(Broken): ${cf.verify(broken)}")

    // 3. transform: drop debug methods and change the 290 constant to 310, as a new class FeeRuleV2
    val newRate = CodeTransform { cob, element ->
        if (element is ConstantInstruction && (element.constantValue() as? Long) == 290L) {
            cob.loadConstant(310L)        // replace this element
        } else {
            cob.with(element)             // pass everything else through unchanged
        }
    }
    val transform = ClassTransform
        .dropping { it is MethodModel && it.methodName().stringValue().startsWith("debug") }
        .andThen(ClassTransform.transformingMethodBodies(newRate))
    val v2 = cf.transformClass(cf.parse(feeRule), ClassDesc.of("FeeRuleV2"), transform)
    val c2 = MethodHandles.lookup().defineClass(v2)
    println("FeeRuleV2 methods ${cf.parse(v2).methods().map { it.methodName().stringValue() }}, " +
        "fee(125000) = ${c2.getMethod("fee", Long::class.javaPrimitiveType).invoke(null, 125_000L)}")
}
