// JDK 24 or later (the ClassFile API is final since JDK 24, JEP 484). From labs/:
//   java bytecode/preview/ClassFileForge.java
// Builds a class from scratch, verifies a broken one, then transforms the first.

import java.lang.classfile.ClassFile;
import java.lang.classfile.ClassModel;
import java.lang.classfile.ClassTransform;
import java.lang.classfile.CodeTransform;
import java.lang.classfile.MethodModel;
import java.lang.classfile.instruction.ConstantInstruction;
import java.lang.constant.ClassDesc;
import java.lang.constant.MethodTypeDesc;
import java.lang.invoke.MethodHandles;

import static java.lang.constant.ConstantDescs.CD_String;
import static java.lang.constant.ConstantDescs.CD_int;
import static java.lang.constant.ConstantDescs.CD_long;
import static java.lang.constant.ConstantDescs.CD_void;

public class ClassFileForge {
    public static void main(String[] args) throws Throwable {
        ClassFile cf = ClassFile.of();

        // 1. build: a class with fee(long) = amount * 290 / 10_000 and a debug method
        byte[] feeRule = cf.build(ClassDesc.of("FeeRule"), clb -> clb
                .withFlags(ClassFile.ACC_PUBLIC | ClassFile.ACC_FINAL)
                .withMethodBody("fee", MethodTypeDesc.of(CD_long, CD_long), ClassFile.ACC_PUBLIC | ClassFile.ACC_STATIC, cob -> cob
                        .lload(0)                 // push the amount (slots 0 and 1)
                        .ldc(290L)                // push the rate in basis points
                        .lmul()
                        .ldc(10_000L)
                        .ldiv()
                        .lreturn())
                .withMethodBody("debugTrace", MethodTypeDesc.of(CD_void, CD_String), ClassFile.ACC_PUBLIC | ClassFile.ACC_STATIC, cob -> cob
                        .return_()));
        System.out.println("built FeeRule: " + feeRule.length + " bytes, verify errors " + cf.verify(feeRule));
        Class<?> c1 = MethodHandles.lookup().defineClass(feeRule);
        System.out.println("FeeRule.fee(125000) = " + c1.getMethod("fee", long.class).invoke(null, 125_000L));

        // 2. verify before you load: an int method that returns a String
        byte[] broken = cf.build(ClassDesc.of("Broken"), clb -> clb
                .withMethodBody("answer", MethodTypeDesc.of(CD_int), ClassFile.ACC_PUBLIC | ClassFile.ACC_STATIC,
                        cob -> cob.ldc("forty-two").ireturn()));
        System.out.println("verify(Broken): " + cf.verify(broken));

        // 3. transform: drop debug methods and change the 290 constant to 310, as a new class FeeRuleV2
        ClassModel model = cf.parse(feeRule);
        CodeTransform newRate = (cob, element) -> {
            if (element instanceof ConstantInstruction ci && Long.valueOf(290L).equals(ci.constantValue())) {
                cob.ldc(310L);            // replace this element
            } else {
                cob.with(element);        // pass everything else through unchanged
            }
        };
        ClassTransform transform = ClassTransform
                .dropping(e -> e instanceof MethodModel m && m.methodName().stringValue().startsWith("debug"))
                .andThen(ClassTransform.transformingMethodBodies(newRate));
        byte[] v2 = cf.transformClass(model, ClassDesc.of("FeeRuleV2"), transform);
        Class<?> c2 = MethodHandles.lookup().defineClass(v2);
        System.out.println("FeeRuleV2 methods " + cf.parse(v2).methods().stream().map(m -> m.methodName().stringValue()).toList()
                + ", fee(125000) = " + c2.getMethod("fee", long.class).invoke(null, 125_000L));
    }
}
