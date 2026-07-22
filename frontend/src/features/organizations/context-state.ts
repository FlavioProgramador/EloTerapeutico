import type {
  Organization,
  OrganizationContextPayload,
  OrganizationMembership,
} from "./types";

export interface OrganizationActivationPayload {
  organization: Organization;
  membership: OrganizationMembership;
}

export function mergeActivatedOrganizationContext(
  current: OrganizationContextPayload | undefined,
  activation: OrganizationActivationPayload,
): OrganizationContextPayload {
  const organizations = [
    activation.organization,
    ...(current?.organizations ?? []).filter(
      (organization) => organization.id !== activation.organization.id,
    ),
  ];

  return {
    active_organization: activation.organization,
    active_membership: activation.membership,
    organizations,
  };
}
