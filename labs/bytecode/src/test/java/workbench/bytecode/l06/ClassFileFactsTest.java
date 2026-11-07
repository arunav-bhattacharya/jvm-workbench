package workbench.bytecode.l06;

import net.bytebuddy.jar.asm.ClassReader;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.TreeSet;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/** The expected values come from ASM (shaded inside Byte Buddy), an independent class-file reader. */
class ClassFileFactsTest {

    static byte[] bytesOf(Class<?> c) throws IOException {
        try (InputStream in = c.getResourceAsStream(c.getSimpleName() + ".class")) {
            return in.readAllBytes();
        }
    }

    static byte[] javaBaseModuleInfo() throws IOException {
        try (InputStream in = Object.class.getModule().getResourceAsStream("module-info.class")) {
            return in.readAllBytes();
        }
    }

    /** ASM's view: every CONSTANT_Class name in the pool. */
    static Set<String> asmClassNames(byte[] bytes) {
        ClassReader r = new ClassReader(bytes);
        char[] buf = new char[r.getMaxStringLength()];
        Set<String> names = new TreeSet<>();
        for (int i = 1; i < r.getItemCount(); i++) {
            int offset = r.getItem(i);                    // start of the entry, after its tag; 0 for a long's second slot
            if (offset > 0 && r.readByte(offset - 1) == 7) names.add(r.readUTF8(offset, buf));
        }
        return names;
    }

    @Test
    @DisplayName("header: magic checked, version 65.0 (release 21), and ASM's constant pool count")
    void headerOfFixture() throws IOException {
        byte[] bytes = bytesOf(Fixture.class);
        ClassFileFacts.Header h = ClassFileFacts.header(bytes);
        assertThat(h.minor()).isZero();
        assertThat(h.major()).isEqualTo(65);
        assertThat(h.constantPoolCount()).isEqualTo(new ClassReader(bytes).getItemCount());
    }

    @Test
    @DisplayName("header: bytes that aren't a class file are rejected because of the magic number")
    void badMagic() {
        byte[] notAClass = "{\"amountMinor\": 1250}".getBytes(StandardCharsets.UTF_8);
        assertThatThrownBy(() -> ClassFileFacts.header(notAClass))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("magic");
    }

    @Test
    @DisplayName("javaVersion: 52 -> 8, 65 -> 21, 69 -> 25, and nothing before Java 5")
    void javaVersions() {
        assertThat(ClassFileFacts.javaVersion(52)).isEqualTo(8);
        assertThat(ClassFileFacts.javaVersion(65)).isEqualTo(21);
        assertThat(ClassFileFacts.javaVersion(69)).isEqualTo(25);
        assertThatThrownBy(() -> ClassFileFacts.javaVersion(46)).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    @DisplayName("javaVersion of a JDK class matches the JDK running the tests")
    void runningJdk() throws IOException {
        int major = ClassFileFacts.header(bytesOf(Long.class)).major();
        assertThat(ClassFileFacts.javaVersion(major)).isEqualTo(Runtime.version().feature());
    }

    @Test
    @DisplayName("thisClass reads past the whole pool: Java, Kotlin and JDK classes")
    void thisClassNames() throws IOException {
        assertThat(ClassFileFacts.thisClass(bytesOf(Fixture.class))).isEqualTo("workbench/bytecode/l06/Fixture");
        assertThat(ClassFileFacts.thisClass(bytesOf(KotlinFixture.class))).isEqualTo("workbench/bytecode/l06/KotlinFixture");
        assertThat(ClassFileFacts.thisClass(bytesOf(Long.class))).isEqualTo("java/lang/Long");
        assertThat(ClassFileFacts.thisClass(bytesOf(Double.class))).isEqualTo("java/lang/Double");
    }

    @Test
    @DisplayName("referencedClasses matches ASM for the fixture, including its lambda and switch")
    void fixtureClasses() throws IOException {
        byte[] bytes = bytesOf(Fixture.class);
        Set<String> names = ClassFileFacts.referencedClasses(bytes);
        assertThat(names).contains("workbench/bytecode/l06/Fixture", "java/util/List", "java/lang/invoke/LambdaMetafactory");
        assertThat(names).isEqualTo(asmClassNames(bytes));
    }

    @Test
    @DisplayName("referencedClasses matches ASM for Kotlin, JDK classes and java.base's module-info (every tag)")
    void everyKindOfEntry() throws IOException {
        for (byte[] bytes : new byte[][]{bytesOf(KotlinFixture.class), bytesOf(Long.class), bytesOf(Double.class),
                bytesOf(java.util.HashMap.class), javaBaseModuleInfo()}) {
            assertThat(ClassFileFacts.referencedClasses(bytes)).isEqualTo(asmClassNames(bytes));
        }
    }
}
