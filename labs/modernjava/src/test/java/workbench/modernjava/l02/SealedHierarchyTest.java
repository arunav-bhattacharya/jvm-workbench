package workbench.modernjava.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.modernjava.l02.LibraryItem.AudioCd;
import workbench.modernjava.l02.LibraryItem.Book;
import workbench.modernjava.l02.LibraryItem.Disc;
import workbench.modernjava.l02.LibraryItem.Dvd;
import workbench.modernjava.l02.LibraryItem.Magazine;
import workbench.modernjava.l02.LibraryItem.PartnerItem;

import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.ToolProvider;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.util.List;
import java.util.Locale;

import static org.assertj.core.api.Assertions.assertThat;

class SealedHierarchyTest {

    // a partner library's own class, written outside the hierarchy's file
    record ArchiveBox(String partnerId, int loanDays) implements PartnerItem {}

    @Test
    @DisplayName("LibraryItem is sealed and permits exactly Book, Disc, Magazine and PartnerItem")
    void libraryItemIsSealed() {
        assertThat(LibraryItem.class.isSealed()).isTrue();
        assertThat(LibraryItem.class.getPermittedSubclasses())
                .containsExactlyInAnyOrder(Book.class, Disc.class, Magazine.class, PartnerItem.class);
    }

    @Test
    @DisplayName("Disc is sealed too, with only Dvd and AudioCd")
    void discIsSealed() {
        assertThat(Disc.class.isSealed()).isTrue();
        assertThat(Disc.class.getPermittedSubclasses()).containsExactlyInAnyOrder(Dvd.class, AudioCd.class);
    }

    @Test
    @DisplayName("PartnerItem stays open, and a partner's own class sets its own loan period")
    void partnerItemIsOpen() {
        assertThat(PartnerItem.class.isSealed()).isFalse();
        assertThat(Loans.loanDays(new ArchiveBox("city-archive", 5))).isEqualTo(5);
        assertThat(Loans.returnBin(new ArchiveBox("city-archive", 5))).isEqualTo("partner:city-archive");
    }

    @Test
    @DisplayName("loanDays: book 21, DVD 7, audio CD 14, magazine 0")
    void loanDays() {
        assertThat(Loans.loanDays(new Book("9780441013593", "Dune"))).isEqualTo(21);
        assertThat(Loans.loanDays(new Dvd("Paddington", 95))).isEqualTo(7);
        assertThat(Loans.loanDays(new AudioCd("Birdsong of the Hills", 18))).isEqualTo(14);
        assertThat(Loans.loanDays(new Magazine("Garden Monthly", 214))).isEqualTo(0);
    }

    @Test
    @DisplayName("returnBin names the bin, with one answer for every kind of disc")
    void returnBin() {
        assertThat(Loans.returnBin(new Book("9780441013593", "Dune"))).isEqualTo("books");
        assertThat(Loans.returnBin(new Dvd("Paddington", 95))).isEqualTo("discs");
        assertThat(Loans.returnBin(new AudioCd("Birdsong of the Hills", 18))).isEqualTo("discs");
        assertThat(Loans.returnBin(new Magazine("Garden Monthly", 214))).isEqualTo("magazines");
    }

    @Test
    @DisplayName("javac accepts a switch with one case per permitted type and no default")
    void exhaustiveSwitchCompiles() throws IOException {
        List<String> errors = compile("Client", """
                package client;
                import workbench.modernjava.l02.LibraryItem;
                import workbench.modernjava.l02.LibraryItem.*;
                class Client {
                    static String f(LibraryItem i) {
                        return switch (i) {
                            case Book b -> "book";
                            case Dvd d -> "dvd";
                            case AudioCd cd -> "cd";
                            case Magazine m -> "magazine";
                            case PartnerItem p -> "partner";
                        };
                    }
                }
                """);
        assertThat(errors).as("javac errors").isEmpty();
    }

    @Test
    @DisplayName("javac rejects a new kind of item or a new kind of disc written outside the hierarchy")
    void outsidersAreRejected() throws IOException {
        List<String> vinyl = compile("Vinyl", """
                package client;
                final class Vinyl implements workbench.modernjava.l02.LibraryItem {}
                """);
        assertThat(vinyl).as("javac errors for Vinyl").singleElement()
                .asString().contains("not allowed to extend sealed class");

        List<String> bluRay = compile("BluRay", """
                package client;
                final class BluRay implements workbench.modernjava.l02.LibraryItem.Disc {}
                """);
        assertThat(bluRay).as("javac errors for BluRay").singleElement()
                .asString().contains("not allowed to extend sealed class");
    }

    /** Compiles one source file against the classes under test and returns javac's error messages. */
    static List<String> compile(String className, String source) throws IOException {
        JavaCompiler javac = ToolProvider.getSystemJavaCompiler();
        assertThat(javac).as("run the tests on a JDK, not a JRE").isNotNull();
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        JavaFileObject file = new SimpleJavaFileObject(
                URI.create("string:///client/" + className + ".java"), JavaFileObject.Kind.SOURCE) {
            @Override
            public CharSequence getCharContent(boolean ignoreEncodingErrors) { return source; }
        };
        String out = Files.createTempDirectory("l02-javac").toString();
        List<String> options = List.of("--release", "21", "-d", out,
                "-classpath", System.getProperty("java.class.path"));
        javac.getTask(null, null, diagnostics, options, null, List.of(file)).call();
        return diagnostics.getDiagnostics().stream()
                .filter(d -> d.getKind() == Diagnostic.Kind.ERROR)
                .map(d -> d.getMessage(Locale.ROOT))
                .toList();
    }
}
