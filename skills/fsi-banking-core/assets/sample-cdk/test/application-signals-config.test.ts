import { App, Stack } from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { ApplicationSignalsConfig } from '../lib/shared/application-signals-config';

describe('ApplicationSignalsConfig', () => {
  let app: App;
  let stack: Stack;

  beforeEach(() => {
    app = new App();
    stack = new Stack(app, 'TestStack', {
      env: {
        region: 'ap-northeast-1',
      },
    });
  });

  describe('SSM Parameter Creation', () => {
    test('creates SSM parameter with correct name', () => {
      // Act
      new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      const template = Template.fromStack(stack);
      template.hasResourceProperties('AWS::SSM::Parameter', {
        Name: '/ecs/cloudwatch-agent/application-signals-config',
        Type: 'String',
        Tier: 'Standard',
      });
    });

    test('creates parameter with correct AWS official configuration', () => {
      // Act
      new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      const template = Template.fromStack(stack);

      // Verify the configuration matches AWS official documentation
      const expectedConfig = {
        traces: {
          traces_collected: {
            application_signals: {},
          },
        },
        logs: {
          metrics_collected: {
            application_signals: {},
          },
        },
      };

      template.hasResourceProperties('AWS::SSM::Parameter', {
        Value: JSON.stringify(expectedConfig),
      });
    });

    test('includes environment and region in description', () => {
      // Act
      new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'production',
        region: 'ap-northeast-3',
      });

      // Assert
      const template = Template.fromStack(stack);
      template.hasResourceProperties('AWS::SSM::Parameter', {
        Description: Match.stringLikeRegexp('.*production.*ap-northeast-3.*'),
      });
    });

    test('applies DESTROY removal policy', () => {
      // Act
      new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      const template = Template.fromStack(stack);
      template.hasResource('AWS::SSM::Parameter', {
        DeletionPolicy: 'Delete',
      });
    });
  });

  describe('Parameter Properties', () => {
    test('exposes parameter name for reference', () => {
      // Act
      const config = new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      expect(config.parameterName).toBe('/ecs/cloudwatch-agent/application-signals-config');
    });

    test('exposes parameter object for IAM permissions', () => {
      // Act
      const config = new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      expect(config.parameter).toBeDefined();
      // Parameter ARN contains SSM service identifier
      expect(config.parameter.parameterArn).toContain(':ssm:');
    });
  });

  describe('Multi-Region Support', () => {
    test('creates parameter in primary region', () => {
      // Arrange
      // 独立した App を使うことで、beforeEach の未使用 TestStack が
      // 一緒に synth され「Resources section must exist and be non-empty」警告が出るのを避ける
      const primaryStack = new Stack(new App(), 'PrimaryStack', {
        env: {
          region: 'ap-northeast-1',
        },
      });

      // Act
      new ApplicationSignalsConfig(primaryStack, 'PrimaryConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      const template = Template.fromStack(primaryStack);
      template.resourceCountIs('AWS::SSM::Parameter', 1);
    });

    test('creates parameter in secondary region', () => {
      // Arrange
      // 独立した App を使うことで、beforeEach の未使用 TestStack が
      // 一緒に synth され「Resources section must exist and be non-empty」警告が出るのを避ける
      const secondaryStack = new Stack(new App(), 'SecondaryStack', {
        env: {
          region: 'ap-northeast-3',
        },
      });

      // Act
      new ApplicationSignalsConfig(secondaryStack, 'SecondaryConfig', {
        envName: 'test',
        region: 'ap-northeast-3',
      });

      // Assert
      const template = Template.fromStack(secondaryStack);
      template.resourceCountIs('AWS::SSM::Parameter', 1);
    });
  });

  describe('Configuration Validation', () => {
    test('configuration includes traces section', () => {
      // Act
      new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      const template = Template.fromStack(stack);
      template.hasResourceProperties('AWS::SSM::Parameter', {
        Value: Match.stringLikeRegexp('.*traces.*traces_collected.*application_signals.*'),
      });
    });

    test('configuration includes logs section', () => {
      // Act
      new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      const template = Template.fromStack(stack);
      template.hasResourceProperties('AWS::SSM::Parameter', {
        Value: Match.stringLikeRegexp('.*logs.*metrics_collected.*application_signals.*'),
      });
    });

    test('configuration is valid JSON', () => {
      // Act
      new ApplicationSignalsConfig(stack, 'TestConfig', {
        envName: 'test',
        region: 'ap-northeast-1',
      });

      // Assert
      const template = Template.fromStack(stack);
      const resources = template.findResources('AWS::SSM::Parameter');
      const parameterResource = Object.values(resources)[0];
      const configValue = parameterResource.Properties.Value;

      // Should not throw when parsing
      expect(() => JSON.parse(configValue)).not.toThrow();

      const parsed = JSON.parse(configValue);
      expect(parsed).toHaveProperty('traces');
      expect(parsed).toHaveProperty('logs');
    });
  });
});
