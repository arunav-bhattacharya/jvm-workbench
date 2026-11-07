package workbench.bytecode.l01;

/** Predict which steps run a static initializer. Each <clinit> prints one indented line. */
public class InitPuzzle {
    static class Parent {
        static int parentValue = 1;
        static { System.out.println("    Parent.<clinit>"); }
    }

    static class Child extends Parent {
        static { System.out.println("    Child.<clinit>"); }
    }

    static class Limits {
        static final int MAX_MINOR = 500_000;     // a constant variable: javac copies 500000 into callers
        static final Integer CAP = 500_000;       // boxed, so not a constant variable
        static { System.out.println("    Limits.<clinit>"); }
    }

    static class Lazy {
        static { System.out.println("    Lazy.<clinit>"); }
        static void touch() {}
    }

    interface Step { void run() throws Exception; }

    static void step(String what, Step s) throws Exception {
        System.out.println(what);
        s.run();
    }

    public static void main(String[] args) throws Exception {
        step("1. read Child.parentValue", () -> { int v = Child.parentValue; });
        step("2. new Child()", () -> new Child());
        step("3. read Limits.MAX_MINOR", () -> { int v = Limits.MAX_MINOR; });
        step("4. read Limits.CAP", () -> { Integer v = Limits.CAP; });
        step("5. new Lazy[3]", () -> { Lazy[] a = new Lazy[3]; });
        step("6. Lazy.class", () -> { Class<?> c = Lazy.class; });
        step("7. Class.forName(name, false, loader)",
                () -> Class.forName("workbench.bytecode.l01.InitPuzzle$Lazy", false, InitPuzzle.class.getClassLoader()));
        step("8. Lazy.touch()", Lazy::touch);
    }
}
