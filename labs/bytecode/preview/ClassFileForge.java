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

        // 1. build: a class with seconds(long steps) = steps * 32 / 1_000 and a debug method
        byte[] fade = cf.build(ClassDesc.of("Fade"), clb -> clb
                .withFlags(ClassFile.ACC_PUBLIC | ClassFile.ACC_FINAL)
                .withMethodBody("seconds", MethodTypeDesc.of(CD_long, CD_long), ClassFile.ACC_PUBLIC | ClassFile.ACC_STATIC, cob -> cob
                        .lload(0)                 // push the number of steps (slots 0 and 1)
                        .ldc(32L)                 // push the length of one step, in milliseconds
                        .lmul()
                        .ldc(1_000L)
                        .ldiv()
                        .lreturn())
                .withMethodBody("debugTrace", MethodTypeDesc.of(CD_void, CD_String), ClassFile.ACC_PUBLIC | ClassFile.ACC_STATIC, cob -> cob
                        .return_()));
        System.out.println("built Fade: " + fade.length + " bytes, verify errors " + cf.verify(fade));
        Class<?> c1 = MethodHandles.lookup().defineClass(fade);
        System.out.println("Fade.seconds(12500) = " + c1.getMethod("seconds", long.class).invoke(null, 12_500L));

        // 2. verify before you load: an int method that returns a String
        byte[] broken = cf.build(ClassDesc.of("Broken"), clb -> clb
                .withMethodBody("answer", MethodTypeDesc.of(CD_int), ClassFile.ACC_PUBLIC | ClassFile.ACC_STATIC,
                        cob -> cob.ldc("forty-two").ireturn()));
        System.out.println("verify(Broken): " + cf.verify(broken));

        // 3. transform: drop debug methods and change the 32 constant to 40, as a new class FadeV2
        ClassModel model = cf.parse(fade);
        CodeTransform slower = (cob, element) -> {
            if (element instanceof ConstantInstruction ci && Long.valueOf(32L).equals(ci.constantValue())) {
                cob.ldc(40L);             // replace this element
            } else {
                cob.with(element);        // pass everything else through unchanged
            }
        };
        ClassTransform transform = ClassTransform
                .dropping(e -> e instanceof MethodModel m && m.methodName().stringValue().startsWith("debug"))
                .andThen(ClassTransform.transformingMethodBodies(slower));
        byte[] v2 = cf.transformClass(model, ClassDesc.of("FadeV2"), transform);
        Class<?> c2 = MethodHandles.lookup().defineClass(v2);
        System.out.println("FadeV2 methods " + cf.parse(v2).methods().stream().map(m -> m.methodName().stringValue()).toList()
                + ", seconds(12500) = " + c2.getMethod("seconds", long.class).invoke(null, 12_500L));
    }
}
