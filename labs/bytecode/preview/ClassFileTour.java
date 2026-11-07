// JDK 24 or later (the ClassFile API is final since JDK 24, JEP 484). From labs/:
//   java bytecode/preview/ClassFileTour.java [path/to/Some.class]
// With no argument it reads StackDemo.class from lesson 2 (run that demo once first),
// or java.lang.Integer from the running JDK if the file isn't there.

import java.lang.classfile.ClassFile;
import java.lang.classfile.ClassModel;
import java.lang.classfile.MethodModel;
import java.lang.classfile.constantpool.PoolEntry;
import java.lang.classfile.instruction.InvokeInstruction;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.TreeMap;

public class ClassFileTour {
    public static void main(String[] args) throws Exception {
        Path p = Path.of(args.length > 0 ? args[0] : "bytecode/build/classes/java/demo/workbench/bytecode/l02/StackDemo.class");
        byte[] bytes = Files.exists(p) ? Files.readAllBytes(p) : Integer.class.getResourceAsStream("Integer.class").readAllBytes();

        // 1. parse: an immutable model, inflated lazily as you ask for parts
        ClassModel cm = ClassFile.of().parse(bytes);
        System.out.println(cm.thisClass().asInternalName() + " extends " + cm.superclass().map(c -> c.asInternalName()).orElse("-")
                + ", major " + cm.majorVersion());

        // 2. the constant pool, counted by kind of entry
        Map<String, Integer> kinds = new TreeMap<>();
        for (PoolEntry e : cm.constantPool()) {
            kinds.merge(e.getClass().getInterfaces()[0].getSimpleName(), 1, Integer::sum);
        }
        System.out.println("constant pool: " + kinds);

        // 3. methods, and the invoke instructions inside each one
        for (MethodModel m : cm.methods()) {
            long invokes = m.code()
                    .map(code -> code.elementStream().filter(e -> e instanceof InvokeInstruction).count())
                    .orElse(0L);
            System.out.println("  " + m.methodName().stringValue() + m.methodType().stringValue() + "  invokes=" + invokes);
        }
    }
}
