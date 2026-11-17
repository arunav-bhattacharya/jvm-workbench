package workbench.patterns.l04;

import java.util.List;

/** The Java twin of ExtensionAdapters.kt. Java has no extension functions, so the adapter is a static method. */
public class ExtensionAdaptersJava {
    // a row from a supplier's price list, with the supplier's names and units
    record SupplierItem(String code, String qty, String unit, String avail) {}

    // our own type
    record Product(String code, long grams, boolean inStock) {}

    // callers write toProduct(item), not item.toProduct(); the mapping still lives in one place
    static Product toProduct(SupplierItem item) {
        double perUnit = switch (item.unit()) {
            case "KG" -> 1_000.0;
            case "LB" -> 453.59237;                 // the supplier abroad still weighs in pounds
            default -> throw new IllegalStateException("unknown unit " + item.unit());
        };
        return new Product(
                item.code(),
                Math.round(Double.parseDouble(item.qty()) * perUnit),
                item.avail().equals("Y"));
    }

    public static void main(String[] args) {
        List<SupplierItem> fromSupplier = List.of(
                new SupplierItem("T-1001", "2.5", "KG", "Y"),
                new SupplierItem("T-1002", "1.5", "LB", "Y"),
                new SupplierItem("T-1003", "10", "KG", "N"));
        fromSupplier.stream().map(ExtensionAdaptersJava::toProduct).forEach(System.out::println);
    }
}
