import { test, expect } from '../../fixtures/auth.fixture';
import { AgentListPage } from '../../pages/agent-list.page';
import { SidebarPage } from '../../pages/sidebar.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generateOrgName, generateAgentData } from '../../helpers/test-data';

test.describe('Agents Organization Isolation', () => {
  let apiClient: ApiClient;
  let createdOrgIds: string[] = [];

  test.beforeEach(async () => {
    apiClient = new ApiClient();
    createdOrgIds = [];
  });

  test.afterEach(async ({ authToken }) => {
    for (const orgId of createdOrgIds) {
      try {
        await apiClient.deleteOrganization(orgId, authToken);
      } catch {
        // Ignore cleanup failures
      }
    }
  });

  test('should show only active org agents when switching', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebar = new SidebarPage(authenticatedPage);
    const listPage = new AgentListPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebar.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs1 = await apiClient.getUserOrgs(authToken);
    const org1 = orgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    const agent1Data = generateAgentData({ name: 'Org1 Agent' });
    await apiClient.createAgent(org1.id, agent1Data, authToken, {
      bypassVerification: 'verified',
    });

    await sidebar.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs2 = await apiClient.getUserOrgs(authToken);
    const org2 = orgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    const agent2Data = generateAgentData({ name: 'Org2 Agent' });
    await apiClient.createAgent(org2.id, agent2Data, authToken, {
      bypassVerification: 'verified',
    });

    await sidebar.switchOrg(org1Name);
    await authenticatedPage.waitForTimeout(500);
    const org1Id = await getOrgIdFromPage(authenticatedPage);
    await listPage.goto(org1Id);
    const cards1 = await listPage.getAgentCards();
    expect(cards1.find((c) => c.name === 'Org1 Agent')).toBeDefined();
    expect(cards1.find((c) => c.name === 'Org2 Agent')).toBeUndefined();

    await sidebar.switchOrg(org2Name);
    await authenticatedPage.waitForTimeout(500);
    const org2Id = await getOrgIdFromPage(authenticatedPage);
    await listPage.goto(org2Id);
    const cards2 = await listPage.getAgentCards();
    expect(cards2.find((c) => c.name === 'Org2 Agent')).toBeDefined();
    expect(cards2.find((c) => c.name === 'Org1 Agent')).toBeUndefined();
  });

  test('should not affect org2 when deleting agent in org1', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebar = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebar.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs1 = await apiClient.getUserOrgs(authToken);
    const org1 = orgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await sidebar.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs2 = await apiClient.getUserOrgs(authToken);
    const org2 = orgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    const agentData = generateAgentData({ name: 'Shared Name Agent' });
    const created1 = await apiClient.createAgent(org1.id, agentData, authToken, {
      bypassVerification: 'verified',
    });
    const created2 = await apiClient.createAgent(org2.id, agentData, authToken, {
      bypassVerification: 'verified',
    });

    await apiClient.deleteAgent(org1.id, created1.id, authToken);

    const agents2 = await apiClient.listAgents(org2.id, authToken);
    expect(agents2.find((a: { id: string }) => a.id === created2.id)).toBeDefined();
  });

  test('should reject cross-org update via API', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebar = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebar.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs1 = await apiClient.getUserOrgs(authToken);
    const org1 = orgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await sidebar.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs2 = await apiClient.getUserOrgs(authToken);
    const org2 = orgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(org1.id, agentData, authToken, {
      bypassVerification: 'verified',
    });

    await expect(
      apiClient.updateAgent(org2.id, created.id, { name: 'Hacked' }, authToken)
    ).rejects.toThrow();

    const agentInOrg1 = await apiClient.getAgent(org1.id, created.id, authToken);
    expect(agentInOrg1.name).toBe(agentData.name);
  });

  test('should reject cross-org delete via API', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebar = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebar.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs1 = await apiClient.getUserOrgs(authToken);
    const org1 = orgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await sidebar.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs2 = await apiClient.getUserOrgs(authToken);
    const org2 = orgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(org1.id, agentData, authToken, {
      bypassVerification: 'verified',
    });

    await expect(apiClient.deleteAgent(org2.id, created.id, authToken)).rejects.toThrow();

    const agents1 = await apiClient.listAgents(org1.id, authToken);
    expect(agents1.find((a: { id: string }) => a.id === created.id)).toBeDefined();
  });

  test('should allow same name in different orgs', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebar = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebar.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs1 = await apiClient.getUserOrgs(authToken);
    const org1 = orgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await sidebar.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs2 = await apiClient.getUserOrgs(authToken);
    const org2 = orgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    const agentData = generateAgentData({ name: 'Support Agent' });
    const created1 = await apiClient.createAgent(org1.id, agentData, authToken, {
      bypassVerification: 'verified',
    });
    const created2 = await apiClient.createAgent(org2.id, agentData, authToken, {
      bypassVerification: 'verified',
    });

    expect(created1.id).not.toBe(created2.id);

    await expect(
      apiClient.createAgent(org1.id, agentData, authToken, {
        bypassVerification: 'verified',
      })
    ).rejects.toThrow();
  });

  test('should return 404 for agent from different org', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebar = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebar.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs1 = await apiClient.getUserOrgs(authToken);
    const org1 = orgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await sidebar.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs2 = await apiClient.getUserOrgs(authToken);
    const org2 = orgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(org1.id, agentData, authToken, {
      bypassVerification: 'verified',
    });

    await expect(apiClient.getAgent(org2.id, created.id, authToken)).rejects.toThrow();
  });
});
