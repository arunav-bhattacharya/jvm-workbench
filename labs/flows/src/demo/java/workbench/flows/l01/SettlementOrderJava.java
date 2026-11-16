// Java equivalent of SettlementOrder.kt. Java has no Flow, so this is a hand-written push "flow":
// the reader calls the ledger writer's Consumer once per line, on the same thread.
package workbench.flows.l01;

import java.util.List;
import java.util.function.Consumer;

public class SettlementOrderJava {
    static void readSettlementFile(List<String> lines, Consumer<String> ledgerWriter) {
        for (String line : lines) {
            String id = line.substring(0, line.indexOf(','));
            System.out.println("read    " + id);
            ledgerWriter.accept(id);
            System.out.println("accept(" + id + ") returned");
        }
    }

    public static void main(String[] args) {
        List<String> lines = List.of("pay-1,4250,EUR", "pay-2,990,EUR", "pay-3,12000,GBP");
        System.out.println("reader ready");

        readSettlementFile(lines, id -> System.out.println("posted  " + id));
        System.out.println("readSettlementFile returned");
    }
}
