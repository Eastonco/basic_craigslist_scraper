import Link from "next/link";
import { Badge, Card, Flex, Heading, Link as RLink, Table, Text } from "@radix-ui/themes";

import { listListingRows } from "../queries";
import GetButton from "./get-button";

export const dynamic = "force-dynamic";

function verdictColor(label: string | null): "green" | "red" | "gray" {
  return label === "want" ? "green" : label === "skip" ? "red" : "gray";
}

export default async function ListingsPage() {
  const rows = await listListingRows(100);
  return (
    <Flex direction="column" gap="4">
      <Heading size="6">Listings</Heading>
      <Card>
        <Table.Root variant="ghost">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeaderCell>When</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Owner</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Verdict</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Title</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell>Reason</Table.ColumnHeaderCell>
              <Table.ColumnHeaderCell></Table.ColumnHeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {rows.map((l) => (
              <Table.Row key={l.id}>
                <Table.Cell>
                  <Text size="1" color="gray">
                    {l.timeScraped || ""}
                  </Text>
                </Table.Cell>
                <Table.Cell>{l.owner ?? "—"}</Table.Cell>
                <Table.Cell>
                  <Badge color={verdictColor(l.aiLabel)}>
                    {l.aiLabel ?? "baseline"}
                    {l.aiScore != null ? ` ${l.aiScore}` : ""}
                  </Badge>
                </Table.Cell>
                <Table.Cell>
                  <RLink asChild>
                    <Link href={`/admin/listings/${l.id}`}>{l.title}</Link>
                  </RLink>
                </Table.Cell>
                <Table.Cell>
                  <Text size="1" color="gray">
                    {l.aiReason || ""}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <GetButton listingId={l.id} link={l.link} size="1" />
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Card>
    </Flex>
  );
}
