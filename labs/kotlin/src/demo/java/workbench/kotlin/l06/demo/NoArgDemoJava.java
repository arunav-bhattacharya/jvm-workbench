package workbench.kotlin.l06.demo;

/**
 * Java twin of NoArgDemo.kt. Java can call the generated constructor directly: it is hidden from
 * Kotlin with @Deprecated(level = HIDDEN), which javac doesn't enforce.
 */
public class NoArgDemoJava {
    public static void main(String[] args) {
        JobRow blank = new JobRow();                         // compiles in Java
        System.out.println("blank.pages = " + blank.getPages());
        System.out.println("blank.status = " + blank.getStatus());   // null: the initializer never ran
        System.out.println("blank.getId() = " + blank.getId());
    }
}
